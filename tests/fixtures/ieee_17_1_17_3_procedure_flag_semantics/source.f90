program ieee_procedure_flag_semantics
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  logical :: observed
  checks = 0
  call prepare(ieee_divide_by_zero)
  call signal_divide_inside()
  call ieee_get_flag(ieee_divide_by_zero, observed)
  call expect_true(observed, 'inside-signal-preserved')
  call expect_count(1)
  write(*,'(a)') 'IEEE 17.1-17.3 PROCEDURE FLAG SEMANTICS SUPPORTED OK'
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
    subroutine signal_divide_inside()
  real, volatile :: one, zero, sink
  one = 1.0
  zero = 0.0
  sink = one / zero
  if (sink == -12345.0) error stop 1
end subroutine signal_divide_inside

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
              write(*,'(a)') 'IEEE17:procedure-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_procedure_flag_semantics
