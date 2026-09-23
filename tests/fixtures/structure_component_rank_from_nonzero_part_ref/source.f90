! rule: S9.4.2-003
! covers: rank-from-nonzero-part-ref
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_rank_from_nonzero_part_ref
  implicit none
  type :: cell_t
    integer :: alpha
    integer :: beta
    integer :: avec(-5:-3)
    integer :: bvec(-5:-3)
    integer :: grid(-4:-2,5:8)
    integer :: other_grid(-4:-2,5:8)
  end type cell_t
  type(cell_t) :: x(2:6)
  integer :: checks
  checks=0
  x(2)%alpha = 311
  x(3)%alpha = 313
  x(4)%alpha = 317
  x(5)%alpha = 319
  x(6)%alpha = 331
  x(2)%beta = 811
  if (x(2)%alpha /= 311) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 811) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:parent-neighbor-x3-control'
    error stop
  end if
  checks=checks+1
  if (x(5)%alpha /= 319) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:parent-neighbor-x5-control'
    error stop
  end if
  checks=checks+1
  if (any(shape(x(2:6:2)%alpha) /= [3])) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:shape'
    error stop
  end if
  checks=checks+1
  if (any(lbound(x(2:6:2)%alpha) /= [1])) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:lbound'
    error stop
  end if
  checks=checks+1
  if (any(ubound(x(2:6:2)%alpha) /= [3])) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:ubound'
    error stop
  end if
  checks=checks+1
  if (any(x(2:6:2)%alpha /= [311, 317, 331])) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:values'
    error stop
  end if
  checks=checks+1
  if (checks /= 8) then
    write(*,'(a)') 'SC:rank_from_nonzero_part_ref:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT RANK FROM NONZERO PART REF OK'
end program structure_component_rank_from_nonzero_part_ref
