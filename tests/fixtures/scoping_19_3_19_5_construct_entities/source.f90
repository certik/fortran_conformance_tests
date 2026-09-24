! rule: S19.4-003
! covers: do-concurrent-forall-index-construct-entity
! covers: associate-select-rank-select-type-name-construct-entity
! covers: local-local-init-construct-entity
! covers: block-declared-entity-construct-entity
! covers: block-use-associated-entity-construct-entity
module scoping_block_use_provider
  implicit none
  integer :: block_use = -606
end module

program scoping_19_3_19_5_construct_entities
  use scoping_block_use_provider, only: module_block_use => block_use
  implicit none
  integer :: checks
  type :: base_t
    integer :: tag = -1
  end type
  type, extends(base_t) :: child_t
    integer :: payload = -2
  end type
  integer :: i, item, x, block_use, local_value, init_value
  integer :: dc_values(3), forall_values(3), target, assoc_seen
  integer :: rank_array(2), rank_seen, type_seen, block_seen, local_seen(1)
  class(base_t), allocatable :: poly
  checks = 0
  i = 99
  item = 98
  x = 97
  block_use = 96
  local_value = 95
  init_value = 7
  dc_values = -1
  forall_values = -2
  target = 10
  assoc_seen = -3
  rank_array = -4
  rank_seen = -5
  type_seen = -6
  block_seen = -7
  local_seen = -8
  module_block_use = -606
  allocate(child_t :: poly)
  do concurrent (i = 1:3)
    dc_values(i) = i
  end do
  forall (i = 1:3)
    forall_values(i) = i + 10
  end forall
  associate (item => target)
    item = 303
    assoc_seen = item
  end associate
  call rank_probe(rank_array, rank_seen)
  select type (item => poly)
  type is (child_t)
    item%tag = 505
    item%payload = 506
    type_seen = item%tag + item%payload
  class default
    type_seen = -5000
  end select
  do concurrent (i = 1:1) local(local_value) local_init(init_value) shared(local_seen)
    local_value = 100
    local_seen(i) = local_value + init_value
    init_value = -77
  end do
  block
    integer :: x
    x = 55
    block_seen = x
  end block
  block
    use scoping_block_use_provider, only: block_use
    block_use = 606
  end block
  if (any(dc_values /= [1, 2, 3])) then
    write(*,'(a)') 'SCOPE:construct_entities:do-concurrent-index'
    error stop
  end if
  checks = checks + 1
  if (any(forall_values /= [11, 12, 13])) then
    write(*,'(a)') 'SCOPE:construct_entities:forall-index'
    error stop
  end if
  checks = checks + 1
  if (target /= 303 .or. assoc_seen /= 303) then
    write(*,'(a)') 'SCOPE:construct_entities:associate-name'
    error stop
  end if
  checks = checks + 1
  if (rank_array(1) /= 404 .or. rank_seen /= 3) then
    write(*,'(a)') 'SCOPE:construct_entities:select-rank-name'
    error stop
  end if
  checks = checks + 1
  if (type_seen /= 1011) then
    write(*,'(a)') 'SCOPE:construct_entities:select-type-name'
    error stop
  end if
  checks = checks + 1
  if (any(local_seen /= [107])) then
    write(*,'(a)') 'SCOPE:construct_entities:local-local-init'
    error stop
  end if
  checks = checks + 1
  if (block_seen /= 55) then
    write(*,'(a)') 'SCOPE:construct_entities:block-declared'
    error stop
  end if
  checks = checks + 1
  if (module_block_use /= 606) then
    write(*,'(a)') 'SCOPE:construct_entities:block-use-associated'
    error stop
  end if
  checks = checks + 1
  if (i /= 99) then
    write(*,'(a)') 'SCOPE:construct_entities:outer-i'
    error stop
  end if
  checks = checks + 1
  if (item /= 98) then
    write(*,'(a)') 'SCOPE:construct_entities:outer-item'
    error stop
  end if
  checks = checks + 1
  if (x /= 97) then
    write(*,'(a)') 'SCOPE:construct_entities:outer-x'
    error stop
  end if
  checks = checks + 1
  if (block_use /= 96) then
    write(*,'(a)') 'SCOPE:construct_entities:outer-block-use'
    error stop
  end if
  checks = checks + 1
  if (local_value /= 95 .or. init_value /= 7) then
    write(*,'(a)') 'SCOPE:construct_entities:outer-locality'
    error stop
  end if
  checks = checks + 1
  if (checks /= 13) then
    write(*,'(a)') 'SCOPE:construct_entities:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 CONSTRUCT ENTITIES OK'
contains
  subroutine rank_probe(a, seen)
    integer, intent(inout) :: a(..)
    integer, intent(inout) :: seen
    select rank (item => a)
    rank (1)
      item(1) = 404
      seen = rank(item) + size(item)
    rank default
      seen = -404
    end select
  end subroutine
end program scoping_19_3_19_5_construct_entities
