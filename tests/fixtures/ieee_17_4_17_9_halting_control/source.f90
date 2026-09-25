program ieee_halting_control_case
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  logical :: observed
  checks = 0
  if (.not. ieee_support_halting(ieee_overflow)) error stop 77
  call ieee_set_halting_mode(ieee_overflow, .false.)
  call ieee_get_halting_mode(ieee_overflow, observed)
  call expect_false(observed, 'halting-false')
  call expect_count(1)
  write(*,'(a)') 'IEEE 17.4-17.9 HALTING CONTROL SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:halting-control-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_halting_control_case
