from django.shortcuts import render
from tfgWeb import models
from tfgWeb import utils, config
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from tfgWeb.forms import UserForm, UserProfileForm
from tfgWeb.forms import InfoForm, UploadForm


def index(request):

    context_dict = {}

    try:
        user = request.user
    except:
        user = None

    experiment_list = models.get_experiments(user)
    context_dict['experiment_list'] = experiment_list

    if request.method == 'POST':

        upload_form = UploadForm(request.POST, request.FILES)

        if (upload_form.is_valid()):

            path = request.FILES['file'].temporary_file_path()

            context_dict['upload_form'] = upload_form

            file = request.FILES['file']
            parts = file.name.split('.')

            if (len(parts) == 1):
                raise ValueError("Type not allowed")
            elif (parts[len(parts) - 1] == 'lif'):
                utils.save_lif(path, request.user)
            elif (parts[len(parts) - 1] == 'h5'):
                utils.save_h5(path, request.user)

            context_dict['upload_form'] = UploadForm()
        else:
            context_dict['upload_form'] = UploadForm()

    return render(request, 'tfgWeb/index.html', context=context_dict)

def experiment(request):

    context_dict = {}

    try:
        selected_experiment = models.get_experiment(request.GET.get('experiment'))
    except:
        experiment_id = request.session['experiment']
        selected_experiment = models.get_experiment(experiment_id)

    series_list = list(selected_experiment.get_galerys())
    atlas_list = list(models.get_atlas())

    context_dict['series'] = series_list
    context_dict['atlas_list'] = atlas_list

    if request.method == 'POST':

        info_form = InfoForm(request.POST)

        if (info_form.is_valid()):

            serieID = int(info_form.cleaned_data['serie'])
            for serie in series_list:
                if serie.id == serieID:
                    selected_serie = serie
                    context_dict['selected_serie'] = selected_serie
                    break

            atlasID = int(info_form.cleaned_data['atlas'])
            for atlas in atlas_list:
                if atlas.id == atlasID:
                    selected_atlas = atlas
                    context_dict['selected_atlas'] = selected_atlas
                    break

            sample_list = selected_serie.get_samples()
            sample_atlas = selected_atlas.get_sample('HIGH')
            samples_allowed = []
            for sample in sample_list:
                if (sample_atlas.x_size >= sample.z_size and sample_atlas.y_size >= sample.x_size and sample_atlas.z_size >= sample.y_size):
                    samples_allowed.append(sample.name)
            if len(samples_allowed)==0:
                raise ValueError("The images are too big for the atlas")
            else:
                context_dict['muestras'] = samples_allowed

            pos_x = info_form.cleaned_data['pos_x']
            pos_y = info_form.cleaned_data['pos_y']
            pos_z = info_form.cleaned_data['pos_z']
            time = info_form.cleaned_data['time']
            selected_sample = info_form.cleaned_data['muestra']

            sample = selected_serie.get_sample(selected_sample)

            context_dict['size_x'] = sample_atlas.x_size
            context_dict['size_y'] = sample_atlas.y_size
            context_dict['size_z'] = sample_atlas.z_size
            context_dict['selected_muestra'] = selected_sample

            front_image = selected_serie.get_image(selected_sample, 'Z', pos_z, time)
            side_image = selected_serie.get_image(selected_sample, 'X', pos_y, time)
            top_image = selected_serie.get_image(selected_sample, 'Y', pos_x, time)

            context_dict['front_image'] = '/' + front_image
            context_dict['top_image'] = '/' + top_image
            context_dict['side_image'] = '/' + side_image

            front_atlas = selected_atlas.get_image(sample_atlas.name, 'X', pos_z, 0)
            side_atlas = selected_atlas.get_image(sample_atlas.name, 'Y', pos_y, 0)
            top_atlas = selected_atlas.get_image(sample_atlas.name, 'Z', pos_x, 0)

            context_dict['front_atlas'] = '/' + front_atlas
            context_dict['top_atlas'] = '/' + top_atlas
            context_dict['side_atlas'] = '/' + side_atlas

            context_dict['pos_x'] = pos_x
            context_dict['pos_y'] = pos_y
            context_dict['pos_z'] = pos_z
            context_dict['time'] = time
            context_dict['total_times'] = selected_serie.total_times - 1
            context_dict['upload_form'] = UploadForm()
            request.session['experiment'] = selected_experiment.id

    else:

        context_dict['pos_x'] = 0
        context_dict['pos_y'] = 0
        context_dict['pos_z'] = 0
        context_dict['time'] = 0
        if series_list:
            context_dict['total_times'] = series_list[0].total_times - 1
            context_dict['selected_serie'] = series_list[0]

            sample_list = series_list[0].get_samples()
            sample_atlas = atlas_list[0].get_sample('HIGH')

            sample_selected = None
            samples_allowed = []
            for sample in sample_list:
                if (sample_atlas.x_size >= sample.x_size and sample_atlas.y_size >= sample.y_size and sample_atlas.z_size >= sample.z_size):
                    sample_selected = sample
                    samples_allowed.append(sample.name)
            if sample_selected == None:
                raise ValueError("The images are too big for the atlas")
            else:
                context_dict['muestras'] = samples_allowed

            context_dict['front_image'] = '/' + series_list[0].get_image(sample_selected.name, 'Z', 0, 0)
            context_dict['top_image'] = '/' + series_list[0].get_image(sample_selected.name, 'Y', 0, 0)
            context_dict['side_image'] = '/' + series_list[0].get_image(sample_selected.name, 'X', 0, 0)
            context_dict['front_atlas'] = '/' + atlas_list[0].get_image(sample_selected.name, 'Z', 0, 0)
            context_dict['side_atlas'] = '/' + atlas_list[0].get_image(sample_selected.name, 'Y', 0, 0)
            context_dict['top_atlas'] = '/' + atlas_list[0].get_image(sample_selected.name, 'X', 0, 0)
            context_dict['selected_muestra'] = sample_selected.name
            context_dict['size_x'] = sample_selected.x_size
            context_dict['size_y'] = sample_selected.y_size
            context_dict['size_z'] = sample_selected.z_size
        context_dict['upload_form'] = UploadForm()
        request.session['experiment'] = selected_experiment.id

    return render(request, 'tfgWeb/experiment.html', context=context_dict)


def info(request):
    context_dict = {}

    try:
        selected_experiment = request.GET.get('experiment')
        context_dict['info'] = selected_experiment.get_info()
    except:
        raise ValueError('Cannot find the experiment')

    return render(request, 'tfgWeb/info.html', context=context_dict)



def register(request):

    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.username = user
            profile.save()
            registered = True

        else:
            print user_form.errors, profile_form.errors
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    return render(request,'tfgWeb/register.html',{'user_form': user_form,'profile_form': profile_form,'registered': registered})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")
    else:
        return render(request, 'tfgWeb/login.html', {})

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))