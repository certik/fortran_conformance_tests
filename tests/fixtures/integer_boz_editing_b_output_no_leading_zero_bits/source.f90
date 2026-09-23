program ibe_b_output_no_leading_zero_bits
  implicit none
! rule: S13.7.2.4-005
! covers: B-output-digits-no-leading-zero-bits
  integer :: checks
  integer :: value
  character(len=5) :: field
  checks = 0
  value = 5
  write(field,'(B5)') value
  call expect_text(field, '  101', 'b5-no-leading')
  if (checks /= 1) then
    write(*,'(a)') 'IBE:b_output_no_leading_zero_bits:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING B OUTPUT NO LEADING ZERO BITS OK'
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
end program ibe_b_output_no_leading_zero_bits
