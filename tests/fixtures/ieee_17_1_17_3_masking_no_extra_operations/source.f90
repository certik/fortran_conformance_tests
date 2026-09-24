program ieee_masking_no_extra_operations
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, zero, y, z
  real :: a(3)
  checks = 0
  one = 1.0
  zero = 0.0
  call prepare(ieee_divide_by_zero)
  z = 0.0
  y = -9.0
  if (zero_function(z) > 0.0) y = one / z
  call expect_real(y, -9.0, 'if-branch-not-executed')
  call expect_flag(ieee_divide_by_zero, .false., 'if-branch-no-divide-flag')
  call prepare(ieee_divide_by_zero)
  a = [2.0, 0.0, -4.0]
  where (a > 0.0) a = one / a
  call expect_real(a(1), 0.5, 'where-positive-updated')
  call expect_real(a(2), 0.0, 'where-zero-masked')
  call expect_real(a(3), -4.0, 'where-negative-masked')
  call expect_flag(ieee_divide_by_zero, .false., 'where-no-divide-flag')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.1-17.3 MASKING NO EXTRA OPERATIONS SUPPORTED OK'
contains

          subroutine prepare(flag)
            type(ieee_flag_type), intent(in) :: flag
            logical :: halting
            if (.not. ieee_support_flag(flag, 0.0)) error stop 77
            if (ieee_support_halting(flag)) then
              call ieee_set_halting_mode(flag, .false.)
            else
              call ieee_get_halting_mode(flag, halting)
              if (halting) error stop 77
            end if
            call ieee_set_flag(flag, .false.)
          end subroutine prepare
    real function zero_function(value)
  real, intent(in) :: value
  zero_function = value
end function zero_function
subroutine expect_real(value, expected, label)
  real, intent(in) :: value, expected
  character(len=*), intent(in) :: label
  if (value /= expected) then
    write(*,'(a,1x,a)') 'IEEE17:real', label
    error stop 1
  end if
  checks = checks + 1
end subroutine expect_real

          subroutine expect_true(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (.not. value) then
              write(*,'(a,1x,a)') 'IEEE17:true', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_true
          subroutine expect_false(value, label)
            logical, intent(in) :: value
            character(len=*), intent(in) :: label
            if (value) then
              write(*,'(a,1x,a)') 'IEEE17:false', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_false
          subroutine expect_flag(flag, expected, label)
            type(ieee_flag_type), intent(in) :: flag
            logical, intent(in) :: expected
            character(len=*), intent(in) :: label
            logical :: observed
            call ieee_get_flag(flag, observed)
            if (observed .neqv. expected) then
              write(*,'(a,1x,a)') 'IEEE17:flag', label
              error stop 1
            end if
            checks = checks + 1
          end subroutine expect_flag
          subroutine expect_count(expected)
            integer, intent(in) :: expected
            if (checks /= expected) then
              write(*,'(a)') 'IEEE17:masking-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_masking_no_extra_operations
