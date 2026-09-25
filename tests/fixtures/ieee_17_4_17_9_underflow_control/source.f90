program ieee_underflow_control_case
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  logical :: saved, observed
  checks = 0
  call require_underflow()
  call expect_true(ieee_support_underflow_control(0.0), 'support-underflow-control')
  call ieee_get_underflow_mode(saved)
  observed = .false.
  call ieee_set_underflow_mode(.true.)
  call ieee_get_underflow_mode(observed)
  call expect_true(observed, 'get-gradual')
  call ieee_set_underflow_mode(.not. saved)
  call ieee_get_underflow_mode(observed)
  call expect_true(observed .neqv. saved, 'set-opposite')
  call ieee_set_underflow_mode(.true.)
  call observe_entry()
  call ieee_set_underflow_mode(saved)
  call expect_count(4)
  write(*,'(a)') 'IEEE 17.4-17.9 UNDERFLOW CONTROL SUPPORTED OK'
contains
  subroutine observe_entry()
    logical :: entry_mode
    call ieee_get_underflow_mode(entry_mode)
    call expect_true(entry_mode, 'entry-gradual')
  end subroutine observe_entry

          subroutine require_underflow()
            logical :: halting
            if (.not. ieee_support_datatype(0.0)) error stop 77
            if (.not. ieee_support_underflow_control(0.0)) error stop 77
            if (.not. ieee_support_subnormal(0.0)) error stop 77
            if (ieee_support_flag(ieee_underflow, 0.0)) then
              if (ieee_support_halting(ieee_underflow)) then
                call ieee_set_halting_mode(ieee_underflow, .false.)
              else
                call ieee_get_halting_mode(ieee_underflow, halting)
                if (halting) error stop 77
              end if
              call ieee_set_flag(ieee_underflow, .false.)
            end if
          end subroutine require_underflow
    
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
              write(*,'(a)') 'IEEE17:underflow-control-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_underflow_control_case
