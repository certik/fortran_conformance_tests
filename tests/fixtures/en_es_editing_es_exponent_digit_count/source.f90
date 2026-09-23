program eee_es_exponent_digit_count
  implicit none
! rule: S13.7.2.3.5-002
! covers: ES-exponent-digit-count
  integer :: checks
  real :: value
  character(len=12) :: field
  checks = 0
  value = 0.125
  field = '############'
  write(field,'(SS,ES12.3E2)') value
  call expect_text(field, '   1.250E-01', 'field')
  if (checks /= 1) then
    write(*,'(a)') 'EEE:es_exponent_digit_count:check-total'
    error stop 1
  end if
  write(*,'(a)') 'EN ES EDITING ES EXPONENT DIGIT COUNT OK'
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
end program eee_es_exponent_digit_count
