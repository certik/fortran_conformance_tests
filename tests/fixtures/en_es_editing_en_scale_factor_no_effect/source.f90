program eee_en_scale_factor_no_effect
  implicit none
! rule: S13.7.2.3.4-001
! covers: EN-scale-factor-no-effect
  integer :: checks
  real :: value
  character(len=12) :: scaled, control
  checks = 0
  value = 0.5
  scaled = '############'
  control = '############'
  write(scaled,'(SS,1P,EN12.3E2)') value
  call expect_text(scaled, ' 500.000E-03', 'scaled')
  write(control,'(SS,0P,EN12.3E2)') value
  call expect_text(control, ' 500.000E-03', 'control')
  if (checks /= 2) then
    write(*,'(a)') 'EEE:en_scale_factor_no_effect:check-total'
    error stop 1
  end if
  write(*,'(a)') 'EN ES EDITING EN SCALE FACTOR NO EFFECT OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'EEE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'EEE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
end program eee_en_scale_factor_no_effect
