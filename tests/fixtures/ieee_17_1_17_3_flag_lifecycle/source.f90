program ieee_flag_lifecycle
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  logical :: observed
  type(ieee_status_type) :: saved
  checks = 0
  call ieee_get_flag(ieee_overflow, observed)
  call expect_false(observed, 'initial-overflow-quiet')
  call prepare(ieee_overflow)
  call ieee_set_flag(ieee_overflow, .true.)
  call ieee_get_flag(ieee_overflow, observed)
  call expect_true(observed, 'set-flag-true')
  call ieee_get_status(saved)
  call ieee_set_flag(ieee_overflow, .false.)
  call ieee_get_flag(ieee_overflow, observed)
  call expect_false(observed, 'set-flag-false')
  call ieee_set_status(saved)
  call ieee_get_flag(ieee_overflow, observed)
  call expect_true(observed, 'set-status-restores')
  call ieee_set_flag(ieee_overflow, .true.)
  call ieee_get_flag(ieee_overflow, observed)
  call expect_true(observed, 'persists-before-clear')
  call ieee_set_flag(ieee_overflow, .false.)
  call ieee_get_flag(ieee_overflow, observed)
  call expect_false(observed, 'persists-until-clear')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.1-17.3 FLAG LIFECYCLE SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:lifecycle-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_flag_lifecycle
