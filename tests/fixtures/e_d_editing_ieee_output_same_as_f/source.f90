program ede_ieee_output_same_as_f
  use, intrinsic :: ieee_arithmetic
  implicit none
! rule: S13.7.2.3.3-003
! covers: E-D-ieee-output-same-as-F
  integer :: checks
  real :: value, nan_value
  character(len=4) :: e_field, d_field, f_field
  character(len=5) :: e_nan, d_nan, f_nan
  checks = 0
  value = ieee_value(0.0, ieee_positive_inf)
  nan_value = ieee_value(0.0, ieee_quiet_nan)
  e_field = '####'
  write(e_field,'(SS,E4.1)') value
  call expect_text(e_field, ' Inf', 'e-inf')
  d_field = '####'
  write(d_field,'(SS,D4.1)') value
  call expect_text(d_field, ' Inf', 'd-inf')
  f_field = '####'
  write(f_field,'(SS,F4.1)') value
  call expect_text(f_field, ' Inf', 'f-inf')
  e_nan = '#####'
  write(e_nan,'(SS,E5.1)') nan_value
  call expect_text(e_nan, '  NaN', 'e-nan')
  d_nan = '#####'
  write(d_nan,'(SS,D5.1)') nan_value
  call expect_text(d_nan, '  NaN', 'd-nan')
  f_nan = '#####'
  write(f_nan,'(SS,F5.1)') nan_value
  call expect_text(f_nan, '  NaN', 'f-nan')
  call expect_true(e_field == f_field, 'e-same-f')
  call expect_true(d_field == f_field, 'd-same-f')
  call expect_true(e_nan == f_nan, 'e-nan-same-f')
  call expect_true(d_nan == f_nan, 'd-nan-same-f')
  if (checks /= 10) then
    write(*,'(a)') 'EDE:ieee_output_same_as_f:check-total'
    error stop 1
  end if
  write(*,'(a)') 'E D EDITING IEEE OUTPUT SAME AS F OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'EDE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'EDE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_one_of(observed, first, second, third, label)
    character(len=*), intent(in) :: observed, first, second, third, label
    if (len(observed) /= len(first) .or. len(observed) /= len(second) .or. len(observed) /= len(third)) then
      write(*,'(a,1x,a)') 'EDE:length', label
      error stop 1
    end if
    if (observed /= first .and. observed /= second .and. observed /= third) then
      write(*,'(a,1x,a)') 'EDE:one-of', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_one_of
  subroutine expect_either(observed, first, second, label)
    character(len=*), intent(in) :: observed, first, second, label
    if (len(observed) /= len(first) .or. len(observed) /= len(second)) then
      write(*,'(a,1x,a)') 'EDE:length', label
      error stop 1
    end if
    if (observed /= first .and. observed /= second) then
      write(*,'(a,1x,a)') 'EDE:either', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_either
  subroutine expect_real(observed, expected, label)
    real, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'EDE:real', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_real
  subroutine expect_true(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (.not. observed) then
      write(*,'(a,1x,a)') 'EDE:logical', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_true
end program ede_ieee_output_same_as_f
