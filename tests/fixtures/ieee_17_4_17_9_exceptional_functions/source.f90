program ieee_exceptional_functions
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, negative_one
  real :: infinity_value, nan_value
  checks = 0
  call require_exceptional()
  one = 1.0
  negative_one = -1.0
  infinity_value = ieee_value(one, ieee_positive_inf)
  nan_value = ieee_value(one, ieee_quiet_nan)
  call expect_false(ieee_is_finite(infinity_value), 'finite-infinity-false')
  call expect_true(ieee_is_nan(nan_value), 'nan-value-true')
  call expect_true(ieee_is_negative(negative_one), 'negative-value-true')
  call expect_false(ieee_is_normal(infinity_value), 'normal-infinity-false')
  call expect_true(ieee_class(ieee_value(one, ieee_positive_inf)) == ieee_positive_inf, 'value-infinity')
  call expect_true(ieee_support_subnormal(one) .and. ieee_support_inf(one) .and. ieee_support_nan(one), 'support-inquiries')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.4-17.9 EXCEPTIONAL FUNCTIONS SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:exceptional-functions-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_exceptional_functions
