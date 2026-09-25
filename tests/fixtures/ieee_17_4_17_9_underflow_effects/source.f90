program ieee_underflow_effects
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  logical :: saved
  real, volatile :: tiny_value, two, result
  checks = 0
  call require_underflow()
  two = 2.0
  tiny_value = tiny(0.0)
  call ieee_get_underflow_mode(saved)
  call ieee_set_underflow_mode(.true.)
  result = tiny_value / two
  call expect_true(ieee_class(result) == ieee_positive_denormal, 'gradual-subnormal')
  call ieee_set_underflow_mode(.false.)
  result = tiny_value / two
  call expect_true(result == 0.0 .and. .not. ieee_is_negative(result), 'abrupt-positive-zero')
  call ieee_set_underflow_mode(saved)
  call expect_count(2)
  write(*,'(a)') 'IEEE 17.4-17.9 UNDERFLOW EFFECTS SUPPORTED OK'
contains

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
              write(*,'(a)') 'IEEE17:underflow-effects-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_underflow_effects
