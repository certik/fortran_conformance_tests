program ieee_status_roundtrip
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  type(ieee_status_type) :: saved_status
  type(ieee_round_type) :: saved_round, observed_round
  logical :: observed_flag
  checks = 0
  call require_status()
  call ieee_get_rounding_mode(saved_round)
  call ieee_set_rounding_mode(ieee_nearest)
  call ieee_set_flag(ieee_overflow, .false.)
  call ieee_get_status(saved_status)
  call ieee_set_flag(ieee_overflow, .true.)
  call ieee_set_rounding_mode(ieee_to_zero)
  call ieee_set_status(saved_status)
  call ieee_get_flag(ieee_overflow, observed_flag)
  call expect_false(observed_flag, 'status-restores-flag')
  call ieee_get_rounding_mode(observed_round)
  call expect_true(observed_round == ieee_nearest, 'status-restores-rounding')
  call ieee_set_rounding_mode(saved_round)
  call expect_count(2)
  write(*,'(a)') 'IEEE 17.4-17.9 STATUS ROUNDTRIP SUPPORTED OK'
contains
  subroutine require_status()
    if (.not. ieee_support_flag(ieee_overflow, 0.0)) error stop 77
    if (.not. ieee_support_rounding(ieee_nearest, 0.0)) error stop 77
    if (.not. ieee_support_rounding(ieee_to_zero, 0.0)) error stop 77
    if (ieee_support_halting(ieee_overflow)) call ieee_set_halting_mode(ieee_overflow, .false.)
  end subroutine require_status

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
              write(*,'(a)') 'IEEE17:status-roundtrip-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_status_roundtrip
