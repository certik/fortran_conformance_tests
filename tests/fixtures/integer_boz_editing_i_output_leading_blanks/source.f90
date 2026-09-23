program ibe_i_output_leading_blanks
  implicit none
! rule: S13.7.2.2-004
! covers: I-output-leading-blanks
  integer :: checks
  integer :: value
  character(len=5) :: field
  checks = 0
  value = 42
  write(field,'(SS,I5)') value
  call expect_text(field, '   42', 'i5-leading')
  if (checks /= 1) then
    write(*,'(a)') 'IBE:i_output_leading_blanks:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING I OUTPUT LEADING BLANKS OK'
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
end program ibe_i_output_leading_blanks
