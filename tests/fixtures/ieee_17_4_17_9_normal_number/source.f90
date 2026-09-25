program ieee_normal_number
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, negative_one
  checks = 0
  if (.not. ieee_support_datatype(0.0)) error stop 77
  one = 1.0
  negative_one = -1.0
  call expect_true(ieee_class(one) == ieee_positive_normal, 'positive-normal-class')
  call expect_true(ieee_class(negative_one) == ieee_negative_normal, 'negative-normal-class')
  call expect_true(ieee_is_normal(one) .and. ieee_is_normal(negative_one), 'is-normal')
  call expect_count(3)
  write(*,'(a)') 'IEEE 17.4-17.9 NORMAL NUMBER SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:normal-number-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_normal_number
