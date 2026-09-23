program rm_data_transfer_specifier_down
  implicit none
! rule: S13.7.2.3.8-001
! covers: round-mode-data-transfer-specifier
  integer :: checks
  real :: transfer_value
  character(len=5) :: transfer_field
  checks = 0
  transfer_value = 1.25
  transfer_field = '#####'
  write(transfer_field,'(SS,F5.1)',round='DOWN') transfer_value
  call expect_text(transfer_field, '  1.2', 'transfer-down')
  if (checks /= 1) then
    write(*,'(a)') 'RM:data_transfer_specifier_down:check-total'
    error stop 1
  end if
  write(*,'(a)') 'ROUNDING MODE DATA TRANSFER SPECIFIER DOWN OK'
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
end program rm_data_transfer_specifier_down
