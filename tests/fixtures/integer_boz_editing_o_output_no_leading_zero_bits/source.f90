program ibe_o_output_no_leading_zero_bits
  implicit none
! rule: S13.7.2.4-005
! covers: O-output-digits-no-leading-zero-bits
  integer :: checks
  integer :: value
  character(len=4) :: field
  checks = 0
  value = 8
  write(field,'(O4)') value
  call expect_text(field, '  10', 'o4-no-leading')
  if (checks /= 1) then
    write(*,'(a)') 'IBE:o_output_no_leading_zero_bits:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING O OUTPUT NO LEADING ZERO BITS OK'
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
end program ibe_o_output_no_leading_zero_bits
