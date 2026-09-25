program ieee_support_divide_case
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, two, half, tiny_value, subnormal_value, inf, qnan, result
  checks = 0
  one = 1.0
  two = 2.0
  half = 0.5
  if (.not. ieee_support_datatype(one)) error stop 77
  if (.not. ieee_support_divide(one)) error stop 77
  if (.not. ieee_support_nan(one)) error stop 77
  if (.not. ieee_support_inf(one)) error stop 77
  if (.not. ieee_support_subnormal(one)) error stop 77
  if (ieee_support_underflow_control(one)) call ieee_set_underflow_mode(.true.)
  tiny_value = tiny(one)
  subnormal_value = tiny_value / two
  inf = ieee_value(one, ieee_positive_inf)
  qnan = ieee_value(one, ieee_quiet_nan)
  call expect_true(ieee_support_divide(one), 'divide-inquiry')
  result = 1.5 / half
  call expect_real(result, 3.0, 'divide-normal')
  result = qnan / one
  call expect_true(ieee_is_nan(result), 'divide-nan')
  result = inf / two
  call expect_true(ieee_class(result) == ieee_positive_inf, 'divide-inf')
  result = tiny_value / two
  call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'divide-subnormal-result')
  result = subnormal_value / one
  call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'divide-subnormal-operand')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT DIVIDE SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:support-divide-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_support_divide_case
