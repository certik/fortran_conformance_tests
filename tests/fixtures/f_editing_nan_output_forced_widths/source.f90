program fe_nan_output_forced_widths
  use, intrinsic :: ieee_arithmetic
  implicit none
! rule: S13.7.2.3.2-011
! covers: nan-output-NaN-right-justified
! covers: nan-output-too-narrow-asterisks
! covers: nan-output-w0-NaN
  integer :: checks
  real :: value
  character(len=5) :: right_field
  character(len=3) :: nan_field
  character(len=2) :: star_field
  checks = 0
  value = ieee_value(0.0, ieee_quiet_nan)
  right_field = '#####'
  write(right_field,'(SS,F5.1)') value
  call expect_text(right_field, '  NaN', 'nan-f5-1')
  nan_field = '###'
  write(nan_field,'(SS,F0.1)') value
  call expect_text(nan_field, 'NaN', 'nan-f0-1')
  star_field = '##'
  write(star_field,'(SS,F2.1)') value
  call expect_text(star_field, '**', 'nan-f2-1')
  if (checks /= 3) then
    write(*,'(a)') 'FE:nan_output_forced_widths:check-total'
    error stop 1
  end if
  write(*,'(a)') 'F EDITING NAN OUTPUT FORCED WIDTHS OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'FE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'FE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_real(observed, expected, label)
    real, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'FE:real', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_real
  subroutine expect_true(observed, label)
    logical, intent(in) :: observed
    character(len=*), intent(in) :: label
    if (.not. observed) then
      write(*,'(a,1x,a)') 'FE:logical', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_true
end program fe_nan_output_forced_widths
