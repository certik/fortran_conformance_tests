! rule: S9.4.2-001
! covers: derived-type-object-part
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_derived_type_object_part
  implicit none
  type :: cell_t
    integer :: alpha
    integer :: beta
    integer :: avec(-5:-3)
    integer :: bvec(-5:-3)
    integer :: grid(-4:-2,5:8)
    integer :: other_grid(-4:-2,5:8)
  end type cell_t
  type(cell_t) :: obj, x(2:6)
  integer :: checks
  checks=0
  x(2)%alpha = 217
  x(3)%alpha = 313
  x(2)%beta = 281
  if (x(2)%alpha /= 217) then
    write(*,'(a)') 'SC:derived_type_object_part:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 281) then
    write(*,'(a)') 'SC:derived_type_object_part:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:derived_type_object_part:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%alpha = 431
  obj%beta = 587
  if (obj%alpha /= 431) then
    write(*,'(a)') 'SC:derived_type_object_part:object-part-alpha'
    error stop
  end if
  checks=checks+1
  if (obj%beta /= 587) then
    write(*,'(a)') 'SC:derived_type_object_part:distinct-neighbor-beta'
    error stop
  end if
  checks=checks+1
  if (checks /= 5) then
    write(*,'(a)') 'SC:derived_type_object_part:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT DERIVED TYPE OBJECT PART OK'
end program structure_component_derived_type_object_part
