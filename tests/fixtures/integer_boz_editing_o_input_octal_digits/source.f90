program ibe_o_input_octal_digits
  implicit none
! rule: S13.7.2.4-003
! covers: O-input-octal-digits
  integer :: checks
  character(len=2) :: field
  integer :: got
  checks = 0
  field = '10'
  read(field,'(O2)') got
  call expect_int(got, 8, 'o2-digits')
  if (checks /= 1) then
    write(*,'(a)') 'IBE:o_input_octal_digits:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING O INPUT OCTAL DIGITS OK'
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
end program ibe_o_input_octal_digits
