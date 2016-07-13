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

    series_list = list(models.get_series(user))
    atlas_list = list(models.get_atlas())
    samples_list = config.RESOLUTIONS.keys()

    context_dict['series'] = series_list
    context_dict['atlas_list'] = atlas_list
    context_dict['muestras'] = samples_list

    if request.method == 'POST':

        info_form = InfoForm(request.POST)
        upload_form = UploadForm(request.POST, request.FILES)

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

            pos_x = info_form.cleaned_data['pos_x']
            pos_y = info_form.cleaned_data['pos_y']
            pos_z = info_form.cleaned_data['pos_z']
            time = info_form.cleaned_data['time']
            selected_sample = info_form.cleaned_data['muestra']
            sample = selected_serie.get_sample(selected_sample)
            context_dict['size_x'] = sample.x_size
            context_dict['size_y'] = sample.y_size
            context_dict['size_z'] = sample.z_size
            context_dict['selected_muestra'] = selected_sample

            front_image = selected_serie.get_image(selected_sample,'Z', pos_z, time)
            side_image = selected_serie.get_image(selected_sample, 'Y', pos_y, time)
            top_image = selected_serie.get_image(selected_sample, 'X', pos_x, time)

            context_dict['front_image'] = '/' + front_image
            context_dict['top_image'] = '/' + top_image
            context_dict['side_image'] = '/' + side_image

            front_atlas = selected_atlas.get_image(selected_sample,'Z', pos_z, 0)
            side_atlas = selected_atlas.get_image(selected_sample, 'Y', pos_y, 0)
            top_atlas = selected_atlas.get_image(selected_sample, 'X', pos_x, 0)

            context_dict['front_atlas'] = '/' + front_atlas
            context_dict['top_atlas'] = '/' + top_atlas
            context_dict['side_atlas'] = '/' + side_atlas

            context_dict['pos_x'] = pos_x
            context_dict['pos_y'] = pos_y
            context_dict['pos_z'] = pos_z
            context_dict['time'] = time
            context_dict['total_times'] = selected_serie.total_times - 1
            context_dict['upload_form'] = UploadForm()

        if (upload_form.is_valid()):

            path = request.FILES['file'].temporary_file_path()

            context_dict['upload_form'] = upload_form

            file = request.FILES['file']
            parts = file.name.split('.')

            if (len(parts)==1):
                raise ValueError("Type not allowed")
            elif (parts[len(parts)-1]=='lif'):
                utils.save_lif(path, request.user)
            elif (parts[len(parts) - 1] == 'h5'):
                utils.save_h5(path, request.user)

            context_dict['front_image'] = None
            context_dict['top_image'] = None
            context_dict['side_image'] = None
            context_dict['pos_x'] = 0
            context_dict['pos_y'] = 0
            context_dict['pos_z'] = 0
            context_dict['time'] = 0
            if series_list:
                series_list[0].total_times -= 1
                context_dict['selected_serie'] = series_list[0]
            context_dict['upload_form'] = UploadForm()
        else:
            context_dict['upload_form'] = UploadForm()
    else:
        context_dict['front_image'] = None
        context_dict['top_image'] = None
        context_dict['side_image'] = None
        context_dict['pos_x'] = 0
        context_dict['pos_y'] = 0
        context_dict['pos_z'] = 0
        context_dict['time'] = 0
        if series_list:
            series_list[0].total_times -= 1
            context_dict['selected_serie'] = series_list[0]
        context_dict['upload_form'] = UploadForm()

    return render(request, 'tfgWeb/index.html', context=context_dict)

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