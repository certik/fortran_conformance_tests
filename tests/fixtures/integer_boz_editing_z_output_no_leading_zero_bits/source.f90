program ibe_z_output_no_leading_zero_bits
  implicit none
! rule: S13.7.2.4-005
! covers: Z-output-digits-no-leading-zero-bits
  integer :: checks
  integer :: value
  character(len=3) :: field
  checks = 0
  value = 10
  write(field,'(Z3)') value
  call expect_text(field, '  A', 'z3-no-leading')
  if (checks /= 1) then
    write(*,'(a)') 'IBE:z_output_no_leading_zero_bits:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING Z OUTPUT NO LEADING ZERO BITS OK'
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
end program ibe_z_output_no_leading_zero_bits
