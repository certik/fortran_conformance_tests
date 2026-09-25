program ieee_support_datatype_core
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, two, half, quarter, qnan
  checks = 0
  one = 1.0
  two = 2.0
  half = 0.5
  quarter = 0.25
  if (.not. ieee_support_datatype(one)) error stop 77
  if (.not. ieee_support_nan(one)) error stop 77
  qnan = ieee_value(one, ieee_quiet_nan)
  call expect_true(ieee_support_datatype(one), 'datatype-inquiry')
  call expect_true(1.5 + quarter == 1.75 .and. 1.5 - quarter == 1.25 .and. 1.5 * half == 0.75, 'normal-ops')
  call expect_true(abs(-1.5) == 1.5 .and. ieee_rem(5.0, two) == one .and. &
    ieee_copy_sign(two, -one) == -two .and. ieee_logb(8.0) == 3.0 .and. &
    .not. ieee_unordered(one, two), 'support-functions')
  call expect_count(3)
  write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT DATATYPE CORE SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:support-datatype-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_support_datatype_core
