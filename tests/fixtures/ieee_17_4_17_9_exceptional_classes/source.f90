program ieee_exceptional_classes
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, two, tiny_value, subnormal_value
  real :: infinity_value, nan_value
  checks = 0
  call require_exceptional()
  one = 1.0
  two = 2.0
  tiny_value = tiny(one)
  subnormal_value = tiny_value / two
  infinity_value = ieee_value(one, ieee_positive_inf)
  nan_value = ieee_value(one, ieee_quiet_nan)
  call expect_true(ieee_class(subnormal_value) == ieee_positive_denormal, 'subnormal-class')
  call expect_true(ieee_class(infinity_value) == ieee_positive_inf, 'infinity-class')
  call expect_true(ieee_is_nan(nan_value), 'nan-class')
  call expect_count(3)
  write(*,'(a)') 'IEEE 17.4-17.9 EXCEPTIONAL CLASSES SUPPORTED OK'
contains

          subroutine require_exceptional()
            if (.not. ieee_support_datatype(0.0)) error stop 77
            if (.not. ieee_support_nan(0.0)) error stop 77
            if (.not. ieee_support_inf(0.0)) error stop 77
            if (.not. ieee_support_subnormal(0.0)) error stop 77
            if (ieee_support_underflow_control(0.0)) call ieee_set_underflow_mode(.true.)
          end subroutine require_exceptional
    
          subroutine expect_true(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (.not. value) then
              write(*,'(a,1x,a)') 'IEEE17:false', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_true
          subroutine expect_false(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (value) then
              write(*,'(a,1x,a)') 'IEEE17:true', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_false
          subroutine expect_real(value, expected, label)
            real, intent(in) :: value, expected
            character(len=*), intent(in) :: label
            if (value /= expected) then
              write(*,'(a,1x,a)') 'IEEE17:real', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_real
          subroutine expect_count(expected)
            integer, intent(in) :: expected
            if (checks /= expected) then
              write(*,'(a)') 'IEEE17:exceptional-classes-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_exceptional_classes
