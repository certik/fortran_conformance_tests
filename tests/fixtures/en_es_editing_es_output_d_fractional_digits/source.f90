program eee_es_output_d_fractional_digits
  implicit none
! rule: S13.7.2.3.5-005
! covers: ES-output-d-fractional-digits
  integer :: checks
  real :: value
  character(len=12) :: field
  checks = 0
  value = 0.5
  field = '############'
  write(field,'(SS,ES12.3E2)') value
  call expect_text(field, '   5.000E-01', 'field')
  if (checks /= 1) then
    write(*,'(a)') 'EEE:es_output_d_fractional_digits:check-total'
    error stop 1
  end if
  write(*,'(a)') 'EN ES EDITING ES OUTPUT D FRACTIONAL DIGITS OK'
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
end program eee_es_output_d_fractional_digits
