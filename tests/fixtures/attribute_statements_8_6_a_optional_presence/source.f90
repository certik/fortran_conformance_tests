module attribute_8_6_a_checks
implicit none
integer :: checked = 0
contains
subroutine check_int(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
  print *, 'CHECK_INT', trim(label), actual, expected
  error stop 1
end if
checked = checked + 1
end subroutine
subroutine check_true(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (.not. actual) then
  print *, 'CHECK_TRUE', trim(label)
  error stop 2
end if
checked = checked + 1
end subroutine
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
  print *, 'CHECK_COUNT', checked, expected
  error stop 3
end if
print '(a)', 'ATTRIBUTE STATEMENTS 8.6.A OK'
end subroutine
end module attribute_8_6_a_checks
program p
        use attribute_8_6_a_checks
        implicit none
        integer :: total
        total = 0
        call observe(10)
        call observe(10, 20, 30)
        call check_int('optional-present-total', total, 60)
        call finish_checks(1)
        contains
        subroutine observe(required, with_colon, plain)
        integer, intent(in) :: required
        integer, intent(in) :: with_colon, plain
        optional :: with_colon
        optional plain
        if (present(with_colon)) then
          total = total + with_colon
        else
          total = total + required
        end if
        if (present(plain)) total = total + plain
        end subroutine observe
end program p
