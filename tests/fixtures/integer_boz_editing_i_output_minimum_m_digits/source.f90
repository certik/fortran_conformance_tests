program ibe_i_output_minimum_m_digits
  implicit none
! rule: S13.7.2.2-005
! covers: I-output-minimum-m-digits
  integer :: checks
  integer :: value
  character(len=5) :: field
  checks = 0
  value = 42
  write(field,'(SS,I5.4)') value
  call expect_text(field, ' 0042', 'i5-4-minimum')
  if (checks /= 1) then
    write(*,'(a)') 'IBE:i_output_minimum_m_digits:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING I OUTPUT MINIMUM M DIGITS OK'
contains
  subroutine expect_text(observed, expected, label)
    character(len=*), intent(in) :: observed, expected, label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'IBE:length', label
      error stop 1
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'IBE:text', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_text
  subroutine expect_int(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'IBE:int', label
      error stop 1
    end if
    checks = checks + 1
  end subroutine expect_int
end program ibe_i_output_minimum_m_digits
