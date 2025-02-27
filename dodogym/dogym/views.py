from django.shortcuts import render

# Create your views here.

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import *
from django.core.paginator import Paginator
from django.db.models import Q
from .models import *
import datetime
from django.utils import timezone
from datetime import timedelta


@login_required
def register_staff(request):
    # ตรวจสอบว่าผู้ใช้เป็น admin หรือ superuser หรือไม่
    if not (request.user.is_superuser or
           (hasattr(request.user, 'staff_profile') and request.user.staff_profile.is_admin)):
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('login')

    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            # สร้าง User ใหม่
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email']
            )

            # สร้าง Staff profile
            staff = Staff.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                is_admin=form.cleaned_data.get('is_admin', False)
            )

            messages.success(request, f'ลงทะเบียนพนักงานใหม่ {user.username} เรียบร้อยแล้ว')
            return redirect('login')
    else:
        form = StaffRegistrationForm()

    return render(request, 'register_staff.html', {'form': form})


def login_view(request):
    # เก็บ URL ที่จะไปหลังจาก login
    next_url = request.POST.get('next', request.GET.get('next', ''))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ถ้ามีการระบุ next_url และมีสิทธิ์เข้าถึง (เป็น superuser หรือ admin)
            if next_url and (user.is_superuser or
                             (hasattr(user, 'staff_profile') and user.staff_profile.is_admin)):
                return redirect(next_url)

            # ถ้าไม่มี next_url หรือไม่มีสิทธิ์เข้าถึง next_url ให้ redirect ตามบทบาท
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif hasattr(user, 'staff_profile'):
                if user.staff_profile.is_admin:
                    return redirect('admin_dashboard')
                else:
                    return redirect('staff_dashboard')
            else:
                logout(request)
                messages.error(request, 'บัญชีนี้ไม่มีสิทธิ์เข้าใช้งานระบบ')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')

    return render(request, 'login.html', {'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def staff_dashboard(request):
    # ตรวจสอบว่าเป็น Staff หรือไม่
    if not hasattr(request.user, 'staff_profile'):
        return redirect('login')

    # โค้ดสำหรับ staff dashboard
    return render(request, 'staff/staff_dashboard.html')


@login_required
def admin_dashboard(request):
    # ตรวจสอบว่าเป็น Admin หรือ superuser หรือไม่
    if not (request.user.is_superuser or
            (hasattr(request.user, 'staff_profile') and request.user.staff_profile.is_admin)):
        return redirect('staff_dashboard')

    # รับพารามิเตอร์จาก URL
    search_query = request.GET.get('search', '')
    user_type = request.GET.get('type', 'all')
    page_number = request.GET.get('page', 1)

    # เริ่มต้นด้วยการดึงข้อมูลทั้งหมด
    staff_users = User.objects.filter(staff_profile__isnull=False)
    members = Member.objects.all()

    # ค้นหาตามคำค้น
    if search_query:
        staff_users = staff_users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

        members = members.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(id_card__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    # กรองตามประเภทผู้ใช้
    if user_type == 'staff':
        members = Member.objects.none()
    elif user_type == 'member':
        staff_users = User.objects.none()

    # รวมข้อมูลเพื่อแสดงผล
    staff_data = [
        {
            'id': user.id,
            'type': 'staff',
            'name': f"{user.first_name} {user.last_name}",
            'username': user.username,
            'email': user.email,
            'role': 'Admin' if hasattr(user, 'staff_profile') and user.staff_profile.is_admin else 'Staff',
            'contact': user.staff_profile.phone_number if hasattr(user, 'staff_profile') else '-',
            'created_at': user.date_joined,
        }
        for user in staff_users
    ]

    member_data = [
        {
            'id': member.id,
            'type': 'member',
            'name': f"{member.first_name} {member.last_name}",
            'username': member.id_card,
            'email': '-',
            'role': 'Member',
            'contact': member.phone_number,
            'created_at': member.created_at,
        }
        for member in members
    ]

    # รวมรายการทั้งหมดและเรียงตามวันที่สร้าง
    all_users = staff_data + member_data
    all_users.sort(key=lambda x: x['created_at'], reverse=True)

    # แบ่งหน้า
    paginator = Paginator(all_users, 10)  # แสดง 10 รายการต่อหน้า
    page_obj = paginator.get_page(page_number)

    # จำนวนผู้ใช้แต่ละประเภท
    staff_count = staff_users.count()
    member_count = members.count()
    total_count = staff_count + member_count

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'user_type': user_type,
        'staff_count': staff_count,
        'member_count': member_count,
        'total_count': total_count,
    }

    return render(request, 'admin_dashboard.html', context)


@login_required
def admin_statistics(request):
    # ตรวจสอบว่าเป็น Admin หรือ superuser หรือไม่
    if not (request.user.is_superuser or
            (hasattr(request.user, 'staff_profile') and request.user.staff_profile.is_admin)):
        return redirect('staff_dashboard')

    # ข้อมูลสถิติเพศ (สำหรับ Pie Chart) - เปลี่ยนจากคีย์ภาษาไทยเป็นอังกฤษ
    gender_data = {
        'male': Member.objects.filter(gender='male').count(),
        'female': Member.objects.filter(gender='female').count(),
        'other': Member.objects.filter(gender='other').count(),
    }

    # ข้อมูลช่วงอายุ (สำหรับ Bar Chart)
    import datetime
    from django.utils import timezone

    today = timezone.now().date()

    # เปลี่ยนจากคีย์ภาษาไทยเป็นอังกฤษ
    age_ranges = {
        'age_0_18': 0,
        'age_19_25': 0,
        'age_26_35': 0,
        'age_36_45': 0,
        'age_46_60': 0,
        'age_60_plus': 0
    }

    # ข้อมูลเพื่อแสดงในกราฟ
    age_labels = ['0-18 ปี', '19-25 ปี', '26-35 ปี', '36-45 ปี', '46-60 ปี', '60+ ปี']

    for member in Member.objects.all():
        age = today.year - member.birth_date.year - (
                    (today.month, today.day) < (member.birth_date.month, member.birth_date.day))
        if age <= 18:
            age_ranges['age_0_18'] += 1
        elif age <= 25:
            age_ranges['age_19_25'] += 1
        elif age <= 35:
            age_ranges['age_26_35'] += 1
        elif age <= 45:
            age_ranges['age_36_45'] += 1
        elif age <= 60:
            age_ranges['age_46_60'] += 1
        else:
            age_ranges['age_60_plus'] += 1

    # ข้อมูลการสมัครสมาชิกรายวัน/เดือน/ปี
    from datetime import timedelta

    # รายวัน (7 วันล่าสุด)
    last_7_days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    daily_registrations = []
    daily_labels = []

    for day in last_7_days:
        day_date = datetime.datetime.strptime(day, '%Y-%m-%d').date()
        count = Member.objects.filter(
            created_at__year=day_date.year,
            created_at__month=day_date.month,
            created_at__day=day_date.day
        ).count()
        daily_labels.append(day_date.strftime('%d/%m/%Y'))
        daily_registrations.append(count)

    # รายเดือน (6 เดือนล่าสุด)
    monthly_registrations = []
    monthly_labels = []
    for i in range(6):
        month_date = today.replace(day=1) - timedelta(days=1) * today.day - timedelta(days=i * 30)
        month_label = month_date.strftime('%B %Y')
        count = Member.objects.filter(
            created_at__year=month_date.year,
            created_at__month=month_date.month
        ).count()
        monthly_labels.append(month_label)
        monthly_registrations.append(count)

    # รายปี (5 ปีล่าสุด)
    yearly_registrations = []
    yearly_labels = []
    current_year = today.year
    for year in range(current_year - 4, current_year + 1):
        count = Member.objects.filter(created_at__year=year).count()
        yearly_labels.append(str(year))
        yearly_registrations.append(count)

    context = {
        'gender_data': gender_data,
        'gender_labels': ['ชาย', 'หญิง', 'อื่นๆ'],
        'age_ranges': age_ranges,
        'age_labels': age_labels,
        'daily_labels': daily_labels,
        'daily_registrations': daily_registrations,
        'monthly_labels': monthly_labels,
        'monthly_registrations': monthly_registrations,
        'yearly_labels': yearly_labels,
        'yearly_registrations': yearly_registrations,
        'total_members': Member.objects.count(),
        'total_staff': User.objects.filter(staff_profile__isnull=False).count(),
    }

    return render(request, 'admin_statistic.html', context)

@login_required
def delete_user(request, user_type, user_id):
    # ตรวจสอบว่าเป็น Admin หรือ superuser หรือไม่
    if not (request.user.is_superuser or
            (hasattr(request.user, 'staff_profile') and request.user.staff_profile.is_admin)):
        messages.error(request, 'คุณไม่มีสิทธิ์ลบผู้ใช้')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        if user_type == 'staff':
            # ป้องกันการลบตัวเอง
            if str(request.user.id) == user_id:
                messages.error(request, 'ไม่สามารถลบบัญชีของตัวเองได้')
            else:
                user = get_object_or_404(User, id=user_id)
                username = user.username
                user.delete()  # ลบ User ซึ่งจะลบ Staff profile ด้วย
                messages.success(request, f'ลบพนักงาน {username} เรียบร้อยแล้ว')

        elif user_type == 'member':
            member = get_object_or_404(Member, id=user_id)
            name = f"{member.first_name} {member.last_name}"
            member.delete()
            messages.success(request, f'ลบสมาชิก {name} เรียบร้อยแล้ว')

    return redirect('admin_dashboard')


def register_member(request):
    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "ลงทะเบียนสมาชิกใหม่สำเร็จ!")
            return redirect('staff_dashboard')
    else:
        form = MemberRegistrationForm()

    return render(request, 'register_member.html', {'form': form})

def add_subscription(request, member_id):
    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        days = int(request.POST.get('days', 0))
        if days > 0:
            last_subscription = Subscription.objects.filter(member=member).order_by('-expiry_date').first()

            if last_subscription and last_subscription.expiry_date > timezone.now():
                expiry_date = last_subscription.expiry_date + timedelta(days=days)
            else:
                expiry_date = timezone.now() + timedelta(days=days)

            Subscription.objects.create(
                member=member,
                days_added=days,
                expiry_date=expiry_date,
                created_by=request.user.staff_profile
            )
            messages.success(request, "เพิ่มวันใช้งานสำเร็จ!")
            return redirect('staff_dashboard')

    return render(request, 'add_subscription.html', {'member': member})

def check_member_status(request):
    query = request.GET.get('query', '')
    member = None

    if query:
        member = Member.objects.filter(id_card=query).first() or Member.objects.filter(phone_number=query).first()

    return render(request, 'check_member_status.html', {'member': member, 'query': query})

def check_member_status(request):
    query = request.GET.get('query', '')
    member = None

    if query:
        member = Member.objects.filter(id_card=query).first() or Member.objects.filter(phone_number=query).first()

    return render(request, 'check_member_status.html', {'member': member, 'query': query})