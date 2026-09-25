! rule: R901
! covers: object-name-alternative array-element-alternative array-section-alternative complex-part-designator-alternative structure-component-alternative substring-alternative
! evidence: positive-control
! standard: f2023
! oracle-basis: standard
program dataobj_designator_forms
  implicit none
  type :: person_t
    integer :: age
    integer :: code
  end type
  integer :: scalar_value, other_scalar, arr(3), section_values(2), checks
  complex :: z
  type(person_t) :: person
  character(len=5) :: text
  checks = 0
  scalar_value = 11
  other_scalar = 12
  arr = [11, 22, 33]
  z = (3.0, 4.0)
  person = person_t(37, 99)
  text = 'abcde'
  call expect_int(scalar_value, 11, 'object name designator')
  call expect_int(arr(2), 22, 'array element designator')
  section_values = arr(1:3:2)
  call expect_int(size(section_values), 2, 'array section extent')
  call expect_int(sum(section_values), 44, 'array section values')
  call expect_int(int(z%im), 4, 'complex part designator')
  call expect_int(person%age, 37, 'structure component designator')
  call expect_char(text(2:4), 'bcd', 'substring designator')
  call expect_int(checks, 7, 'check count before completion')
  write(*,'(a)') 'DATA OBJECTS DESIGNATOR FORMS OK'
contains
  subroutine expect_true(ok, label)
    logical, intent(in) :: ok
    character(len=*), intent(in) :: label
    if (.not. ok) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_int(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'DATAOBJ-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_char(observed, expected, label)
    character(len=*), intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (len(observed) /= len(expected)) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL-LEN', label
      error stop
    end if
    if (observed /= expected) then
      write(*,'(a,1x,a)') 'DATAOBJ-FAIL-CHAR', label
      error stop
    end if
    checks = checks + 1
  end subroutine
end program dataobj_designator_forms
