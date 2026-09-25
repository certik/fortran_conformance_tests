program ieee_support_nan_case
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, qnan, result
  checks = 0
  one = 1.0
  if (.not. ieee_support_datatype(one)) error stop 77
  if (.not. ieee_support_nan(one)) error stop 77
  qnan = ieee_value(one, ieee_quiet_nan)
  call expect_true(ieee_support_nan(one), 'nan-inquiry')
  result = qnan + one
  call expect_true(ieee_is_nan(result), 'nan-plus')
  result = qnan - one
  call expect_true(ieee_is_nan(result), 'nan-minus')
  result = qnan * one
  call expect_true(ieee_is_nan(result), 'nan-times')
  result = ieee_rem(qnan, one)
  call expect_true(ieee_is_nan(result), 'nan-rem')
  result = ieee_rint(qnan)
  call expect_true(ieee_is_nan(result), 'nan-rint')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT NAN SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:support-nan-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_support_nan_case
