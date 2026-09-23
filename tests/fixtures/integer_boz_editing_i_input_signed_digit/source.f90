program ibe_i_input_signed_digit
  implicit none
! rule: S13.7.2.2-003
! covers: I-input-signed-digit-string
  integer :: checks
  character(len=3) :: field_negative, field_positive
  integer :: got_negative, got_positive
  checks = 0
  field_negative = '-42'
  field_positive = ' 42'
  read(field_negative,'(I3)') got_negative
  call expect_int(got_negative, -42, 'i3-negative')
  read(field_positive,'(I3)') got_positive
  call expect_int(got_positive, 42, 'i3-positive')
  if (checks /= 2) then
    write(*,'(a)') 'IBE:i_input_signed_digit:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING I INPUT SIGNED DIGIT OK'
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
end program ibe_i_input_signed_digit
