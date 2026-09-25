program ieee_rounding_entry
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  type(ieee_round_type) :: saved
  checks = 0
  call require_rounding()
  call ieee_get_rounding_mode(saved)
  call ieee_set_rounding_mode(ieee_up)
  call observe_entry()
  call ieee_set_rounding_mode(saved)
  call expect_count(1)
  write(*,'(a)') 'IEEE 17.4-17.9 ROUNDING ENTRY SUPPORTED OK'
contains
  subroutine observe_entry()
    type(ieee_round_type) :: entry_mode
    call ieee_get_rounding_mode(entry_mode)
    call expect_true(entry_mode == ieee_up, 'entry-rounding-up')
  end subroutine observe_entry

          subroutine require_rounding()
            if (radix(0.0) /= 2) error stop 77
            if (.not. ieee_support_rounding(ieee_nearest, 0.0)) error stop 77
            if (.not. ieee_support_rounding(ieee_to_zero, 0.0)) error stop 77
            if (.not. ieee_support_rounding(ieee_up, 0.0)) error stop 77
            if (.not. ieee_support_rounding(ieee_down, 0.0)) error stop 77
          end subroutine require_rounding
    
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
              write(*,'(a)') 'IEEE17:rounding-entry-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_rounding_entry
