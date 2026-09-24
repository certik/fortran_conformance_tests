program ieee_class_constants_core
  use, intrinsic :: ieee_arithmetic, only: ieee_class_type, &
    ieee_signaling_nan, ieee_quiet_nan, ieee_negative_inf, ieee_negative_normal, &
    ieee_negative_subnormal, ieee_negative_zero, ieee_positive_zero, &
    ieee_positive_subnormal, ieee_positive_normal, ieee_positive_inf, &
    ieee_other_value, ieee_negative_denormal, ieee_positive_denormal, &
    operator(==), operator(/=)
  implicit none
  integer :: checks
  type(ieee_class_type) :: classes(11)
  checks = 0
  classes = [ieee_signaling_nan, ieee_quiet_nan, ieee_negative_inf, &
    ieee_negative_normal, ieee_negative_subnormal, ieee_negative_zero, &
    ieee_positive_zero, ieee_positive_subnormal, ieee_positive_normal, &
    ieee_positive_inf, ieee_other_value]
  call expect_true(all(classes(1:10) /= classes(2:11)), 'class-listed-distinct')
  call expect_true(ieee_negative_denormal == ieee_negative_subnormal, 'negative-denormal-alias')
  call expect_true(ieee_positive_denormal == ieee_positive_subnormal, 'positive-denormal-alias')
  call expect_true(ieee_positive_zero /= ieee_negative_zero, 'class-comparable')
  call expect_count(4)
  write(*,'(a)') 'IEEE 17.1-17.3 CLASS CONSTANTS CORE SUPPORTED OK'
contains
  subroutine expect_true(value, label)
    logical, intent(in) :: value
    character(len=*), intent(in) :: label
    if (.not. value) then
      write(*,'(a,1x,a)') 'IEEE17:false', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_true
  subroutine expect_count(expected)
    integer, intent(in) :: expected
    if (checks /= expected) then
      write(*,'(a)') 'IEEE17:class-count'
      error stop 1
    end if
  end subroutine expect_count
end program ieee_class_constants_core
