program rm_edit_descriptor_specifier_zero
  implicit none
! rule: S13.7.2.3.8-001
! covers: round-mode-edit-descriptor
  integer :: checks
  real :: descriptor_value
  character(len=5) :: descriptor_field
  checks = 0
  descriptor_value = 1.25
  descriptor_field = '#####'
  write(descriptor_field,'(SS,RZ,F5.1)') descriptor_value
  call expect_text(descriptor_field, '  1.2', 'descriptor-rz')
  if (checks /= 1) then
    write(*,'(a)') 'RM:edit_descriptor_specifier_zero:check-total'
    error stop 1
  end if
  write(*,'(a)') 'ROUNDING MODE EDIT DESCRIPTOR SPECIFIER ZERO OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'RM:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'RM:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_real(observed, expected, label)
    real, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'RM:real', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_real
end program rm_edit_descriptor_specifier_zero
