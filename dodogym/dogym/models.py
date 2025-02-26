from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # สำหรับเก็บข้อมูลว่าเป็น Admin หรือ Staff ปกติ
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {'Admin' if self.is_admin else 'Staff'}"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def email(self):
        return self.user.email


class Member(models.Model):
    GENDER_CHOICES = (
        ('male', 'ชาย'),
        ('female', 'หญิง'),
        ('other', 'อื่นๆ'),
    )

    first_name = models.CharField(max_length=100, verbose_name="ชื่อ")
    last_name = models.CharField(max_length=100, verbose_name="นามสกุล")
    id_card = models.CharField(max_length=13, unique=True, verbose_name="รหัสบัตรประชาชน")
    birth_date = models.DateField(verbose_name="วันเดือนปีเกิด")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="เพศ")
    weight = models.FloatField(verbose_name="น้ำหนัก (กก.)")
    height = models.FloatField(verbose_name="ส่วนสูง (ซม.)")
    phone_number = models.CharField(max_length=15, verbose_name="เบอร์โทร")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.birth_date.year - (
                    (today.month, today.day) < (self.birth_date.month, self.birth_date.day))


class Subscription(models.Model):


    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='subscriptions', verbose_name="สมาชิก")
    days_added = models.PositiveIntegerField(verbose_name="จำนวนวันที่เพิ่ม")
    paid_date = models.DateTimeField(default=timezone.now, verbose_name="วันที่บันทึก")
    expiry_date = models.DateTimeField(verbose_name="วันที่หมดอายุ")
    created_by = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, related_name='subscriptions_created',
                                   verbose_name="ผู้บันทึกข้อมูล")

    def __str__(self):
        return f"{self.member} - {self.days_added} วัน ({self.paid_date.strftime('%d/%m/%Y')})"

    def save(self, *args, **kwargs):
        # คำนวณวันหมดอายุโดยอัตโนมัติเมื่อบันทึก
        if not self.expiry_date:
            # ถ้ามีการต่ออายุ ให้ต่อจากวันหมดอายุเดิม
            last_subscription = Subscription.objects.filter(
                member=self.member
            ).exclude(id=self.id).order_by('-expiry_date').first()

            if last_subscription and last_subscription.expiry_date > timezone.now():
                # ถ้ามีการต่ออายุก่อนหมด ให้ต่อจากวันที่หมดอายุเดิม
                self.expiry_date = last_subscription.expiry_date + timezone.timedelta(days=self.days_added)
            else:
                # ถ้าหมดอายุไปแล้ว ให้เริ่มนับจากวันที่บันทึก
                self.expiry_date = self.paid_date + timezone.timedelta(days=self.days_added)

        super().save(*args, **kwargs)