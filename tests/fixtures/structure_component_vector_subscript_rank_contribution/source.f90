! rule: S9.4.2-002
! covers: vector-subscript-rank-contribution
! Expected values, bounds and shapes are hand-derived from Fortran 2023 9.4.2.
program structure_component_vector_subscript_rank_contribution
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
  integer :: picks(2)
  checks=0
  x(2)%alpha = 251
  x(3)%alpha = 313
  x(2)%beta = 307
  if (x(2)%alpha /= 251) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:parent-subscript-control'
    error stop
  end if
  checks=checks+1
  if (x(2)%beta /= 307) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:component-peer-control'
    error stop
  end if
  checks=checks+1
  if (x(3)%alpha /= 313) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:parent-neighbor-control'
    error stop
  end if
  checks=checks+1
  obj%grid(-2,8) = 284
  obj%grid(-4,8) = 484
  obj%grid(-3,8) = 384
  obj%other_grid(-2,8) = 784
  obj%other_grid(-4,8) = 684
  picks = [-2, -4]
  if (any(shape(obj%grid(picks,8)) /= [2])) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:shape'
    error stop
  end if
  checks=checks+1
  if (any(lbound(obj%grid(picks,8)) /= [1])) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:lbound'
    error stop
  end if
  checks=checks+1
  if (any(ubound(obj%grid(picks,8)) /= [2])) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:ubound'
    error stop
  end if
  checks=checks+1
  if (any(obj%grid(picks,8) /= [284, 484])) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:values'
    error stop
  end if
  checks=checks+1
  if (obj%grid(-3,8) /= 384) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:vector-feature-value-control'
    error stop
  end if
  checks=checks+1
  if (obj%other_grid(-2,8) /= 784) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:other-grid-first-control'
    error stop
  end if
  checks=checks+1
  if (obj%other_grid(-4,8) /= 684) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:other-grid-second-control'
    error stop
  end if
  checks=checks+1
  if (checks /= 10) then
    write(*,'(a)') 'SC:vector_subscript_rank_contribution:check-total'
    error stop
  end if
  write(*,'(a)') 'STRUCTURE COMPONENT VECTOR SUBSCRIPT RANK CONTRIBUTION OK'
end program structure_component_vector_subscript_rank_contribution
