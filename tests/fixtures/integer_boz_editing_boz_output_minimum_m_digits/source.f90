program ibe_boz_output_minimum_m_digits
  implicit none
! rule: S13.7.2.4-007
! covers: BOZ-output-minimum-m-digits
  integer :: checks
  integer :: b_value, o_value, z_value
  character(len=4) :: b_field, o_field, z_field
  checks = 0
  b_value = 5
  o_value = 8
  z_value = 10
  write(b_field,'(B4.4)') b_value
  call expect_text(b_field, '0101', 'b4-4-minimum')
  write(o_field,'(O4.4)') o_value
  call expect_text(o_field, '0010', 'o4-4-minimum')
  write(z_field,'(Z4.4)') z_value
  call expect_text(z_field, '000A', 'z4-4-minimum')
  if (checks /= 3) then
    write(*,'(a)') 'IBE:boz_output_minimum_m_digits:check-total'
    error stop 1
  end if
  write(*,'(a)') 'INTEGER BOZ EDITING BOZ OUTPUT MINIMUM M DIGITS OK'
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
end program ibe_boz_output_minimum_m_digits
