program eee_en_exponent_divisible_by_three
  implicit none
! rule: S13.7.2.3.4-001
! covers: EN-exponent-divisible-by-three
  integer :: checks
  real :: value
  character(len=12) :: field
  checks = 0
  value = 0.5
  field = '############'
  write(field,'(SS,EN12.3E2)') value
  call expect_text(field, ' 500.000E-03', 'field')
  if (checks /= 1) then
    write(*,'(a)') 'EEE:en_exponent_divisible_by_three:check-total'
    error stop 1
  end if
  write(*,'(a)') 'EN ES EDITING EN EXPONENT DIVISIBLE BY THREE OK'
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
end program eee_en_exponent_divisible_by_three
