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
        type :: pair_t
          integer :: left
          integer :: right
        end type pair_t
        integer :: basis, literal, named, vector(2)
        type(pair_t) :: pair
        logical explicit_logical
        parameter (basis=3)
        parameter (literal=7, named=basis+4)
        parameter (vector=[3,7])
        parameter (pair=pair_t(11,13))
        parameter (explicit_logical=.true.)
        call late_implicit
        call check_int('parameter-literal', literal, 7)
        call check_int('parameter-named-expression', named, 7)
        call check_true('parameter-prior-explicit-logical', explicit_logical)
        call check_true('parameter-vector-shape', all(shape(vector) == [2]))
        call check_int('parameter-vector-element', vector(2), 7)
        call check_int('parameter-derived-left', pair%left, 11)
        call check_int('parameter-derived-right', pair%right, 13)
        call finish_checks(8)
        contains
        subroutine late_implicit
        implicit integer(n)
        parameter (n=2)
        integer n
        call check_int('parameter-late-matching-integer', n, 2)
        end subroutine late_implicit
end program p
