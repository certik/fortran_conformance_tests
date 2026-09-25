program ieee_support_sqrt_case
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks, e
  real, volatile :: one, zero, neg_zero, inf, qnan, x, expected, result
  checks = 0
  one = 1.0
  zero = 0.0
  if (.not. ieee_support_datatype(one)) error stop 77
  if (.not. ieee_support_sqrt(one)) error stop 77
  if (.not. ieee_support_nan(one)) error stop 77
  if (.not. ieee_support_inf(one)) error stop 77
  if (.not. ieee_support_subnormal(one)) error stop 77
  if (ieee_support_underflow_control(one)) call ieee_set_underflow_mode(.true.)
  neg_zero = ieee_copy_sign(zero, -one)
  inf = ieee_value(one, ieee_positive_inf)
  qnan = ieee_value(one, ieee_quiet_nan)
  e = minexponent(one) - 2
  e = e - modulo(e, 2)
  if (e < minexponent(one) - digits(one)) error stop 77
  x = scale(one, e)
  expected = scale(one, e / 2)
  call expect_true(ieee_support_sqrt(one), 'sqrt-inquiry')
  result = sqrt(neg_zero)
  call expect_true(result == zero .and. ieee_is_negative(result), 'sqrt-negative-zero')
  result = sqrt(qnan)
  call expect_true(ieee_is_nan(result), 'sqrt-nan')
  result = sqrt(inf)
  call expect_true(ieee_class(result) == ieee_positive_inf, 'sqrt-inf')
  call expect_true(ieee_class(x) == ieee_positive_denormal, 'sqrt-subnormal-precheck')
  result = sqrt(x)
  call expect_real(result, expected, 'sqrt-subnormal')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT SQRT SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:support-sqrt-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_support_sqrt_case
