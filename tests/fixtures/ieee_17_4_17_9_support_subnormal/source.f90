program ieee_support_subnormal_case
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, zero, tiny_value, two, subnormal_value, result
  checks = 0
  one = 1.0
  zero = 0.0
  two = 2.0
  if (.not. ieee_support_datatype(one)) error stop 77
  if (.not. ieee_support_subnormal(one)) error stop 77
  if (ieee_support_underflow_control(one)) call ieee_set_underflow_mode(.true.)
  tiny_value = tiny(one)
  subnormal_value = tiny_value / two
  call expect_true(ieee_support_subnormal(one), 'subnormal-inquiry')
  call expect_true(ieee_class(subnormal_value) == ieee_positive_denormal, 'subnormal-precheck')
  result = subnormal_value + zero
  call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'subnormal-add')
  result = tiny_value - subnormal_value
  call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'subnormal-subtract')
  result = subnormal_value * one
  call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'subnormal-multiply')
  result = ieee_rem(subnormal_value, two * tiny_value)
  call expect_true(result == subnormal_value .and. ieee_class(result) == ieee_positive_denormal, 'subnormal-rem')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT SUBNORMAL SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:support-subnormal-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_support_subnormal_case
