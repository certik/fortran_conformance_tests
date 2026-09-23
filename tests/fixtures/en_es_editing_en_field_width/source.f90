program eee_en_field_width
  implicit none
! rule: S13.7.2.3.4-002
! covers: EN-field-width
  integer :: checks
  real :: value
  character(len=12) :: field
  checks = 0
  value = 100.0
  field = '############'
  write(field,'(SS,EN12.3E2)') value
  call expect_text(field, ' 100.000E+00', 'field')
  if (checks /= 1) then
    write(*,'(a)') 'EEE:en_field_width:check-total'
    error stop 1
  end if
  write(*,'(a)') 'EN ES EDITING EN FIELD WIDTH OK'
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
end program eee_en_field_width
