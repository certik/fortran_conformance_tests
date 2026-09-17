subroutine character_entity(n)
implicit none
integer, intent(in) :: n
character, save :: text*(n)
text='x'
end subroutine character_entity
