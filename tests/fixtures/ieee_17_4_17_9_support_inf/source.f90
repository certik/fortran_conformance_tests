program ieee_support_inf_case
  use, intrinsic :: ieee_arithmetic
  implicit none
  integer :: checks
  real, volatile :: one, two, inf, ninf, result
  checks = 0
  one = 1.0
  two = 2.0
  if (.not. ieee_support_datatype(one)) error stop 77
  if (.not. ieee_support_inf(one)) error stop 77
  inf = ieee_value(one, ieee_positive_inf)
  ninf = ieee_value(one, ieee_negative_inf)
  call expect_true(ieee_support_inf(one), 'inf-inquiry')
  result = inf + one
  call expect_true(ieee_class(result) == ieee_positive_inf, 'inf-plus')
  result = one - inf
  call expect_true(ieee_class(result) == ieee_negative_inf, 'one-minus-inf')
  result = ninf * two
  call expect_true(ieee_class(result) == ieee_negative_inf, 'ninf-times')
  result = ieee_rem(1.5, inf)
  call expect_real(result, 1.5, 'finite-rem-inf')
  result = ieee_rint(inf)
  call expect_true(ieee_class(result) == ieee_positive_inf, 'rint-inf')
  call expect_count(6)
  write(*,'(a)') 'IEEE 17.4-17.9 SUPPORT INF SUPPORTED OK'
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
              write(*,'(a)') 'IEEE17:support-inf-count'
              error stop 1
            end if
          end subroutine expect_count
    end program ieee_support_inf_case
