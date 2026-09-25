program ieee_support_standard_case
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  logical :: any_rounding
  checks = 0
  if (.not. ieee_support_standard(0.0)) error stop 77
  any_rounding = ieee_support_rounding(ieee_nearest, 0.0) .or. &
    ieee_support_rounding(ieee_to_zero, 0.0) .or. ieee_support_rounding(ieee_up, 0.0) .or. &
    ieee_support_rounding(ieee_down, 0.0)
  call expect_true(ieee_support_standard(0.0), 'standard-inquiry')
  call expect_true(ieee_support_datatype(0.0) .and. ieee_support_nan(0.0) .and. &
    ieee_support_inf(0.0) .and. ieee_support_subnormal(0.0) .and. &
    ieee_support_divide(0.0) .and. ieee_support_sqrt(0.0) .and. &
    ieee_support_underflow_control(0.0) .and. any_rounding, 'standard-implies')
  call expect_count(2)
  write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT STANDARD SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:support-standard-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_support_standard_case
