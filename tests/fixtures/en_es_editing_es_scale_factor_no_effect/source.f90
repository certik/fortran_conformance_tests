program eee_es_scale_factor_no_effect
  implicit none
! rule: S13.7.2.3.5-001
! covers: ES-scale-factor-no-effect
  integer :: checks
  real :: value
  character(len=12) :: scaled, control
  checks = 0
  value = 0.5
  scaled = '############'
  control = '############'
  write(scaled,'(SS,2P,ES12.3E2)') value
  call expect_text(scaled, '   5.000E-01', 'scaled')
  write(control,'(SS,0P,ES12.3E2)') value
  call expect_text(control, '   5.000E-01', 'control')
  if (checks /= 2) then
    write(*,'(a)') 'EEE:es_scale_factor_no_effect:check-total'
    error stop 1
  end if
  write(*,'(a)') 'EN ES EDITING ES SCALE FACTOR NO EFFECT OK'
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
end program eee_es_scale_factor_no_effect
