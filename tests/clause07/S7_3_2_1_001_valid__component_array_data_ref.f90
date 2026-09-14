! rule: S7.3.2.1-001
! covers: component-array-data-ref
! evidence: effect
! standard: f2023
program typeof_component_array
    implicit none
    type :: record
        character(3) :: text
    end type
    type(record) :: records(2)
    typeof(records%text) :: scalar
    typeof(records(2)%text) :: element
    records(1)%text = 'abc'
    records(2)%text = 'def'
    scalar = 'XYZ'
    element = 'uvw'
    if (rank(scalar) /= 0 .or. rank(element) /= 0) error stop 'rank-not-inherited'
    if (len(scalar) /= 3 .or. len(element) /= 3) error stop 'length'
    if (kind(scalar) /= kind('a') .or. kind(element) /= kind('a')) error stop 'kind'
    if (scalar /= 'XYZ' .or. element /= 'uvw') error stop 'copies'
    if (records(1)%text /= 'abc' .or. records(2)%text /= 'def') error stop 'sources'
end program
