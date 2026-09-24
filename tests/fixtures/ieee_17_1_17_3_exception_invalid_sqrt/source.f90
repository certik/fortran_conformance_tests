program ieee_exception_invalid_sqrt
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: negative, sink
  checks = 0
  negative = -1.0
  call prepare(ieee_invalid)
  sink = sqrt(negative)
  call expect_flag(ieee_invalid, .true., 'invalid-sqrt-flag')
  call expect_true(ieee_is_nan(sink), 'invalid-sqrt-nan')
  call expect_count(2)
  write(*,'(a)') 'IEEE 17.1-17.3 EXCEPTION INVALID SQRT SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:invalid-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_exception_invalid_sqrt
