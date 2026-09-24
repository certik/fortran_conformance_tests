! rule: S15.2.1-002
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module elemental_reference_m
  implicit none
contains
  elemental integer function inc(x)
    integer, intent(in) :: x
    inc = x + 1
  end function
end module
program elemental_reference
  use elemental_reference_m
  implicit none
  integer :: result(2)
  result = [-777, -778]
  result = inc([1, 41])
  if (any(result /= [2, 42])) error stop 1
  print '(a)', 'PROCEDURES 15.2.1 ELEMENTAL REFERENCE OK'
end program
