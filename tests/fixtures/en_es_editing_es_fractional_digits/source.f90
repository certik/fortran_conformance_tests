program eee_es_fractional_digits
  implicit none
! rule: S13.7.2.3.5-002
! covers: ES-fractional-digits
  integer :: checks
  real :: value
  character(len=11) :: field
  checks = 0
  value = 100.0
  field = '###########'
  write(field,'(SS,ES11.2E2)') value
  call expect_text(field, '   1.00E+02', 'field')
  if (checks /= 1) then
    write(*,'(a)') 'EEE:es_fractional_digits:check-total'
    error stop 1
  end if
  write(*,'(a)') 'EN ES EDITING ES FRACTIONAL DIGITS OK'
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
end program eee_es_fractional_digits
